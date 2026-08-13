using Newsletter.Worker.Modelos;
using Newsletter.Worker.Servicos;

namespace Newsletter.Tests;

/// <summary>
/// Parsing da fila: o payload usado aqui é exatamente o que
/// `EdicaoPublica.model_dump(mode="json")` produz do lado Python.
/// Nenhum teste toca Redis — a desserialização é estática e pura.
/// </summary>
public class FilaParsingTests
{
    private const string PayloadDaCuradoria = """
    {
      "data": "2026-08-13",
      "gerada_em": "2026-08-13T08:30:00",
      "total": 3,
      "topicos": [
        {
          "chave": "vistos",
          "rotulo": "Vistos",
          "itens": [
            {
              "titulo": "Nuove regole per il visto studio",
              "url": "https://esempio.it/visto",
              "fonte": "google_news",
              "resumo": "Il consolato aggiorna le regole.",
              "publicada_em": "2026-08-13T06:00:00"
            }
          ]
        },
        {
          "chave": "bolsas",
          "rotulo": "Bolsas",
          "itens": [
            {
              "titulo": "Bando DSU 2026/2027",
              "url": "https://laziodisco.it/bando",
              "fonte": "laziodisco",
              "resumo": null,
              "publicada_em": null
            }
          ]
        }
      ]
    }
    """;

    [Fact]
    public void Desserializa_o_payload_da_curadoria()
    {
        var edicao = FilaRedis.Desserializar(PayloadDaCuradoria);

        Assert.NotNull(edicao);
        Assert.Equal(new DateOnly(2026, 8, 13), edicao.Data);
        Assert.Equal(3, edicao.Total);
        Assert.Equal(2, edicao.Topicos.Count);
    }

    [Fact]
    public void Preserva_a_ordem_dos_topicos_definida_pela_curadoria()
    {
        var edicao = FilaRedis.Desserializar(PayloadDaCuradoria)!;

        Assert.Equal(["vistos", "bolsas"], edicao.Topicos.Select(t => t.Chave));
    }

    [Fact]
    public void Le_os_campos_snake_case_do_item()
    {
        var item = FilaRedis.Desserializar(PayloadDaCuradoria)!.Topicos[0].Itens[0];

        Assert.Equal("Nuove regole per il visto studio", item.Titulo);
        Assert.Equal("google_news", item.Fonte);
        Assert.Equal(new DateTime(2026, 8, 13, 6, 0, 0), item.PublicadaEm);
    }

    [Fact]
    public void Aceita_resumo_e_data_nulos()
    {
        var item = FilaRedis.Desserializar(PayloadDaCuradoria)!.Topicos[1].Itens[0];

        Assert.Null(item.Resumo);
        Assert.Null(item.PublicadaEm);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData("   ")]
    [InlineData("{ isso não é json }")]
    [InlineData("{\"data\": \"2026-08-13\"}")] // faltam campos obrigatórios
    public void Payload_invalido_vira_null_em_vez_de_derrubar_o_worker(string? bruto)
    {
        Assert.Null(FilaRedis.Desserializar(bruto));
    }

    [Fact]
    public void Edicao_sem_topicos_e_valida()
    {
        const string vazia = """
        {"data":"2026-08-13","gerada_em":"2026-08-13T08:30:00","total":0,"topicos":[]}
        """;

        var edicao = FilaRedis.Desserializar(vazia);

        Assert.NotNull(edicao);
        Assert.Empty(edicao.Topicos);
    }
}
