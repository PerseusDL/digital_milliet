from digital_milliet.lib.oauth import OAuthHelper
from flask import render_template, request, redirect, session, flash, Response, g
from bson.json_util import dumps
from flask_babel import gettext


class Views(object):
    def __init__(
            self,
            app=None,
            commentaries=None,
            db=None,
            authors=None,
            mirador=None):
        """ Main view system

        :param app: Flask APP
        :type app: Flask
        :param commentaries: Commentary Component
        :type commentaries: CommentaryHandler
        :param db: Mongo Data Resolver
        :type db: PyMongo
        :param authors: Author Component
        :type authors: AuthorBuilder
        :param mirador: Mirador Component
        :type mirador: Mirador
        """
        self.app = app
        self.commentaries = commentaries
        self.mongo = db
        self.authors = authors
        self.mirador = mirador

        self.add_lang_url_rule('/', view_func=self.index)
        self.add_lang_url_rule('/index', view_func=self.index)
        self.add_lang_url_rule('/about', view_func=self.about)
        self.add_lang_url_rule(
            '/search',
            view_func=self.search,
            methods=['GET'])
        self.add_lang_url_rule('/commentary', view_func=self.commentary)
        self.add_lang_url_rule('/commentary/<millnum>', view_func=self.millnum)
        self.add_lang_url_rule('/edit/<millnum>', view_func=self.edit)
        self.add_lang_url_rule(
            '/edit/save_edit',
            view_func=self.save_edit,
            methods=['POST'])
        self.add_lang_url_rule(
            '/delete',
            view_func=self.delete,
            methods=['POST'])
        self.add_lang_url_rule(
            '/create',
            view_func=self.create,
            methods=['POST'])
        self.add_lang_url_rule(
            '/api/commentary/<millnum>',
            view_func=self.api_data_get,
            methods=['GET'])
        self.add_lang_url_rule(
            '/api/tags/<type>',
            view_func=self.api_tags_get,
            methods=['GET'])
        self.add_lang_url_rule(
            '/new',
            view_func=self.new,
            methods=[
                'GET',
                'POST'],
            strict_slashes=False)

        @app.route('/favicon.ico')
        def favicon():
            return app.send_static_file('favicon/favicon.ico')

        @app.before_request
        def before():
            if request.view_args and 'lang' in request.view_args:
                g.lang = request.view_args['lang']
                request.view_args.pop('lang')

    def add_lang_url_rule(self, rule, **options):
        self.app.add_url_rule(rule, **options)
        self.app.add_url_rule('/<lang>' + rule, **options)

    def index(self):
        return render_template('index.html')

    def about(self):
        return render_template('about.html')

    def search(self):
        """ Search results
        """
        query = request.args.get("query")
        res = None
        type = request.args.get("in")
        if query:
            if type == "Author":
                res = self.authors.search(query=query, name=True)
            elif type == "Title":
                res = self.authors.search(query=query, works=True)
            else:
                res = self.commentaries.search(query=query, tags=True)
            try:
                if res.count() == 0:
                    res = None
            except BaseException:
                if len(res) == 0:
                    res = None

        return render_template('search.html', res=res, type=type)

    def commentary(self):
        """ List available commentaries and Milliet entries
        """
        millnum_list = self.commentaries.get_milliet_identifier_list()
        auth_list = self.authors.author_list()
        return render_template(
            'commentary/list.html',
            millnum_list=millnum_list,
            auth_list=auth_list)

    def millnum(self, millnum):
        """ Read a Milliet entry
        """
        parsed_obj, auth_info = self.commentaries.get_milliet(millnum)
        if 'orig_uri' in parsed_obj:
            session['cts_uri'] = parsed_obj['orig_uri']
        (previous_millnum,
         next_millnum) = self.commentaries.get_surrounding_identifier(millnum)

        return render_template(
            'commentary/read.html',
            obj=parsed_obj,
            info=auth_info,
            millnum=millnum,
            previous_millnum=previous_millnum,
            next_millnum=next_millnum)

    @OAuthHelper.oauth_required
    def delete(self):
        millnum = request.form['millnum']
        removed = self.commentaries.remove_milliet(millnum)
        if removed > 0:
            flash(
                gettext(
                    'Record for %(millnum)s removed.',
                    millnum=millnum),
                'success')
        else:
            flash(
                gettext(
                    'Error removing record for %(millnum)s.',
                    millnum=millnum),
                'danger')
        return redirect('commentary')

    @OAuthHelper.oauth_required
    def edit(self, millnum):
        """ Edit the Milliet identified by millnum
        """
        parsed_obj, auth_info = self.commentaries.get_milliet(millnum)

        return render_template(
            'commentary/edit.html',
            millnum=millnum,
            obj=parsed_obj)

    @OAuthHelper.oauth_required
    def save_edit(self):
        """ Save the edit form
        """
        form = request.form.to_dict()
        if "iiif[]" in form:
            form["iiif"] = request.form.getlist("iiif[]")
            form["iiif_publisher"] = request.form.getlist("iiif_publisher[]")
        if "tags" in form:
            form["tags"] = request.form.get("tags").split()
        else:
            form["tags"] = []
        if "semantic_tags" in form:
            form["semantic_tags"] = request.form.get("semantic_tags").split()
        else:
            form["semantic_tags"] = []
        saved = self.commentaries.update_commentary(form)
        if saved:
            flash(gettext('Edit successfully saved'), 'success')
        else:
            flash(gettext('Error!'), 'danger')

        return redirect('commentary')

    @OAuthHelper.oauth_required
    def create(self):
        """ Create a new entry
        """
        data = request.form.to_dict()
        if "iiif[]" in data:
            data["iiif"] = request.form.getlist("iiif[]")
            data["iiif_publisher"] = request.form.getlist("iiif_publisher[]")
        if "tags" in data:
            data["tags"] = request.form.get("tags").split()
        else:
            data["tags"] = []
        if "semantic_tags" in data:
            data["semantic_tags"] = request.form.get("semantic_tags").split()
        else:
            data["semantic_tags"] = []
        millnum = self.commentaries.create_commentary(data)
        if millnum is not None:
            flash(gettext('Annotation successfully created!'), 'success')
            return redirect('commentary/' + str(millnum))
        else:
            flash(gettext('Error saving!'), 'danger')
            return redirect('new')

    def api_data_get(self, millnum):
        """ Read a Milliet entry as a JSON Bag
        """
        res = self.commentaries.get_milliet(milliet_id=millnum, simplify=False)
        res["iiif_annotations"] = self.mirador.from_collection(millnum)
        return self.mirador.dump(res)

    @OAuthHelper.oauth_required
    def new(self):
        return render_template(
            'commentary/create.html',
            cts_api=self.app.config['CTS_API_URL'],
            cts_browse=self.app.config['CTS_BROWSE_URL'],
            cts_version=self.app.config['CTS_API_VERSION']
        )

    def api_tags_get(self, type):
        """ Get the existing tags """
        tags, semantic_tags = self.commentaries.get_existing_tags()
        if type == 'semantic':
            json = [{'value': tag} for tag in semantic_tags]
        else:
            json = [{'value': tag} for tag in tags]
        return Response(
            dumps(json),
            mimetype='application/json',
            status=200
        )
