from django import forms

from wiki.models import Article, Tag


class ArticleForm(forms.ModelForm):
    """Форма статьи для редактирования прямо на сайте (не в админке).

    Теги — одной строкой через запятую: касса, возврат. Так кассиру
    не нужен мультиселект, а нам не нужна виджет-магия.
    """

    tags_input = forms.CharField(
        label='Теги', required=False,
        help_text='Через запятую, например: касса, возврат')

    class Meta:
        model = Article
        fields = ['title', 'category', 'body', 'is_draft']
        widgets = {
            'body': forms.Textarea(attrs={
                'rows': 18,
                'id': 'id_body',
                'placeholder': 'Заголовок: ## Текст… Ссылка: [текст](https://…)'
                               ' Картинка: кнопка «🖼» ниже',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_input'].initial = ', '.join(
                self.instance.tags.values_list('name', flat=True))

    def save(self, commit=True):
        article = super().save(commit=commit)
        raw = self.cleaned_data.get('tags_input', '').replace(';', ',')
        names = []
        for part in raw.split(','):
            name = part.strip().lstrip('#').strip().lower()
            if name and name not in names:
                names.append(name)
        tags = [Tag.objects.get_or_create(name=n)[0] for n in names]
        article.tags.set(tags)
        return article
