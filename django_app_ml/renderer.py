from rest_framework.renderers import BrowsableAPIRenderer, TemplateHTMLRenderer



class CustomScoringAppTemplateRenderer(BrowsableAPIRenderer):
    """
    This rendered allow to override default rest framework template keeping
    BrowsableAPI view with all its fonctions (forms, results, etc....)
    """
    template = "scoring_app/base.html"
    js_base = "ml_app/static/ml_app/js/main.js"
    
    def get_context(self, data, accepted_media_type, renderer_context):
        context = super().get_context(data, accepted_media_type, renderer_context)
        context['js_base'] = f"http://localhost:3000/{self.js_base}"
        return context