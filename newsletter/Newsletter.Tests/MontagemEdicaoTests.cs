using System.Text.Json;
using Newsletter.Worker.Modelos;
using Newsletter.Worker.Servicos;

namespace Newsletter.Tests;

/// <summary>
/// Montagem da edição: serialização de ida e volta, assunto e renderização do
/// HTML. O renderizador só lê o template do disco — não há rede nem SMTP aqui.
/// </summary>
public class MontagemEdicaoTests
{
    private static Edicao EdicaoExemplo(int itens = 1) => new()
    {
        Data = new DateOnly(2026, 8, 13),
        GeradaEm = new DateTime(2026, 8, 13, 8, 30, 0),
        Total = itens,
        Topicos =
        [
            new TopicoEdicao
            {
                Chave = "vistos",
                Rotulo = "Vistos",
                Itens = Enumerable.Range(1, itens).Select(i => new ItemEdicao
                {
                    Titulo = $"Regra de visto {i}",
                    Url = $"https://esempio.it/visto-{i}",
                    Fonte = "google_news",
                    Resumo = "Resumo da notícia.",
                    PublicadaEm = new DateTime(2026, 8, 13, 6, 0, 0),
                }).ToList(),
            },
        ],
    };

    [Fact]
    public void Serializacao_de_ida_e_volta_preserva_a_edicao()
    {
        var original = EdicaoExemplo(itens: 2);

        var json = JsonSerializer.Serialize(original);
        var reconstruida = FilaRedis.Desserializar(json);

        // records comparam listas por REFERÊNCIA, então a igualdade estrutural
        // é verificada pelo JSON reserializado — e campo a campo abaixo
        Assert.NotNull(reconstruida);
        Assert.Equal(json, JsonSerializer.Serialize(reconstruida));
        Assert.Equal(original.Data, reconstruida.Data);
        Assert.Equal(original.GeradaEm, reconstruida.GeradaEm);
        Assert.Equal(original.Total, reconstruida.Total);
        Assert.Equal(original.Topicos[0], reconstruida.Topicos[0] with
        {
            Itens = original.Topicos[0].Itens,
        });
        Assert.Equal(original.Topicos[0].Itens, reconstruida.Topicos[0].Itens);
    }

    [Fact]
    public void Serializa_com_as_chaves_snake_case_do_contrato()
    {
        var json = JsonSerializer.Serialize(EdicaoExemplo());

        Assert.Contains("\"gerada_em\"", json);
        Assert.Contains("\"publicada_em\"", json);
        Assert.DoesNotContain("\"GeradaEm\"", json);
    }

    [Fact]
    public void Assunto_traz_a_data_e_a_contagem()
    {
        var assunto = AssuntoEdicao.Para(EdicaoExemplo(itens: 4));

        Assert.Equal("Ponte Italia · 13/08/2026 · 4 destaque(s) para sua jornada", assunto);
    }

    [Fact]
    public async Task Renderiza_o_html_com_os_topicos_e_os_itens()
    {
        var html = await new RenderizadorRazor().RenderizarAsync(EdicaoExemplo(itens: 2));

        Assert.Contains("Ponte", html);
        Assert.Contains("Vistos", html);
        Assert.Contains("Regra de visto 1", html);
        Assert.Contains("Regra de visto 2", html);
        Assert.Contains("https://esempio.it/visto-1", html);
        Assert.Contains("13/08/2026", html);
    }

    [Fact]
    public async Task Renderiza_aviso_quando_a_edicao_nao_tem_topicos()
    {
        var vazia = new Edicao
        {
            Data = new DateOnly(2026, 8, 13),
            GeradaEm = new DateTime(2026, 8, 13, 8, 30, 0),
            Total = 0,
            Topicos = [],
        };

        var html = await new RenderizadorRazor().RenderizarAsync(vazia);

        Assert.Contains("Nenhuma notícia se encaixou", html);
    }

    [Fact]
    public async Task Usa_a_paleta_de_pergaminho_do_logo()
    {
        var html = await new RenderizadorRazor().RenderizarAsync(EdicaoExemplo());

        Assert.Contains("#F2E5D5", html); // creme do papel
        Assert.Contains("#BFAE99", html); // bege das bordas
        Assert.Contains("#797963", html); // sálvia dos filetes
        Assert.Contains("#1B1A18", html); // tinta
    }

    [Fact]
    public async Task Traz_o_link_para_a_noticia_original()
    {
        var html = await new RenderizadorRazor().RenderizarAsync(EdicaoExemplo(itens: 2));

        Assert.Contains("https://esempio.it/visto-1", html);
        Assert.Contains("Ler a notícia completa", html);
    }

    [Fact]
    public async Task Escreve_a_data_por_extenso_em_portugues()
    {
        var html = await new RenderizadorRazor().RenderizarAsync(EdicaoExemplo());

        // independe do idioma da máquina que roda o worker
        Assert.Contains("13 de agosto de 2026", html);
    }
}
