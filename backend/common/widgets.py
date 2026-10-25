from django import forms


class SearchableSelect(forms.Select):
    def __init__(self, attrs=None, choices=()):
        super().__init__({**(attrs or {}), "data-searchable": "true"}, choices)

    class Media:
        js = ("resources/search-select.js",)
