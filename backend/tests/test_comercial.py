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

def test_proposta_completa_e_campos_longos():
    dados = {
        "cliente": "Empresa Exemplo", "projeto": "Site institucional",
        "objetivo": "Apresentar soluções da empresa.", "servicos": "Site responsivo",
        "beneficios": "Facilitar o contato.", "etapas": "Briefing e aprovação.",
        "inicial": "800", "mensal": "90", "prazo": "7 dias",
        "pagamento": "Conforme contratação", "validade": "7 dias",
        "recorrencia": "Manutenção conforme plano.", "responsabilidades": "Enviar materiais.",
        "limites": "Custos externos à parte.", "observacoes": "Detalhes do escopo.\n" * 120,
        "incluir_detalhes": True,
    }
    pdf = gerar_proposta_pdf({"nome": "Empresa Exemplo"}, dados)
    assert pdf.startswith(b"%PDF")
    with pytest.raises(ValueError):
        gerar_proposta_pdf({}, {**dados, "objetivo": "x" * 4001})


def test_modelo_compacto_solar():
    pdf = gerar_proposta_pdf({"nome": "ENERGIA SLZ", "categoria": "Energia solar"}, {
        "cliente": "ENERGIA SLZ - ENERGIA SOLAR", "projeto": "Desenvolvimento de site profissional",
        "servicos": "Design personalizado\nLayout responsivo\nApresentação institucional\nIntegração com WhatsApp\nTestes e publicação",
        "inicial": "199.99", "mensal": "90", "prazo": "7 dias após o recebimento dos materiais e aprovação do escopo",
        "pagamento": "Valor inicial conforme acordado. Mensalidade com vencimento definido na contratação.",
        "validade": "7 dias", "incluir_detalhes": False,
    })
    assert pdf.startswith(b"%PDF")
    assert b"/Count 1" in pdf


def test_instagram_normalizado():
    from rotas_comercial import normalizar_instagram
    assert normalizar_instagram("@empresa.exemplo") == "https://www.instagram.com/empresa.exemplo/"
    assert normalizar_instagram("https://instagram.com/empresa.exemplo/?igsh=123") == "https://www.instagram.com/empresa.exemplo/"
    assert normalizar_instagram("") is None
    with pytest.raises(ValueError):
        normalizar_instagram("https://example.com/perfil")


def test_proposta_com_qr_instagram():
    pdf = gerar_proposta_pdf({"nome": "Empresa Teste"}, {
        "servicos": "Design personalizado\nLayout responsivo\nApresentação institucional\nIntegração com WhatsApp\nTestes e publicação",
        "inicial": "0", "mensal": "90", "prazo": "7 dias após receber os materiais e aprovar o escopo",
        "pagamento": "Valor inicial conforme acordado. Mensalidade com vencimento definido na contratação.",
        "validade": "7 dias", "instagram_flp": "@empresa.exemplo",
    })
    assert pdf.startswith(b"%PDF")
    assert b"/Count 1" in pdf
    assert b"https://www.instagram.com/empresa.exemplo/" in pdf
