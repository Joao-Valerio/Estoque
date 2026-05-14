from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("website", "0003_produto_quantidade_produto_quantidade_minima"),
    ]

    operations = [
        migrations.AddField(
            model_name="movimentacao",
            name="destinatario",
            field=models.CharField(
                blank=True,
                default="",
                max_length=200,
                verbose_name="Destinatário",
            ),
        ),
        migrations.AddField(
            model_name="movimentacao",
            name="fornecedor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="movimentacoes_entrada",
                to="website.fornecedor",
                verbose_name="Fornecedor",
            ),
        ),
    ]
