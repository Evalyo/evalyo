from django.views.generic import TemplateView


class TitledTemplateView(TemplateView):
    title = None

    def get_context_data(self, **kwargs):
        if "title" not in kwargs and self.title is not None:
            kwargs["title"] = self.title
        return super().get_context_data(**kwargs)
