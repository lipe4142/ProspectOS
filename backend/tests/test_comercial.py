from decimal import Decimal
import pytest
from rotas_comercial import _valor, gerar_proposta_pdf


def test_proposta_pdf():
    pdf = gerar_proposta_pdf({"nome": "Empresa Teste"}, {
        "cliente": "Empresa Teste", "servicos": "Site responsivo", "inicial": "0",
        "mensal": "90", "prazo": "7 dias", "pagamento": "Mensal", "validade": "7 dias",
    })
    assert pdf.startswith(b"%PDF")


@pytest.mark.parametrize("valor", ["NaN", "Infinity", "-1", "0.001", "abc"])
def test_rejeita_valores_invalidos(valor):
    with pytest.raises(ValueError):
        _valor({"mensal": valor}, "mensal")


def test_valor_decimal():
    assert _valor({"mensal": "90.50"}, "mensal") == Decimal("90.50")


def test_demonstracao_sem_ia(monkeypatch):
    from flask import Flask
    import rotas_comercial as comercial
    app = Flask(__name__)
    app.register_blueprint(comercial.bp)
    monkeypatch.setattr(comercial, "_lead", lambda _: {"nome": "Empresa Teste", "categoria": "Imobiliária"})
    def falhar(*args, **kwargs):
        raise comercial.ia.NenhumProvedorDisponivel(None)
    monkeypatch.setattr(comercial.ia, "executar_com_fallback", falhar)
    resposta = app.test_client().post("/api/leads/abc/demonstracao", json={"identidade": "Azul", "servicos": "Venda de imóveis"})
    assert resposta.status_code == 200
    assert "Empresa Teste" in resposta.json["briefing"]
    assert "Venda de imóveis" in resposta.json["prompt"]
    assert resposta.json["provedor"] is None
