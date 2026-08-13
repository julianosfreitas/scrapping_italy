using System.Net.Http.Headers;
using System.Net.Http.Json;
using System.Text.Json;
using Microsoft.Extensions.Options;
using Newsletter.Worker.Configuracao;
using Newsletter.Worker.Modelos;

namespace Newsletter.Worker.Servicos;

public interface IClientePonteApi
{
    Task<IReadOnlyList<string>> InscritosAtivosAsync(CancellationToken cancelamento);

    Task MarcarEnviadaAsync(DateOnly data, CancellationToken cancelamento);
}

/// <summary>
/// Cliente da API do site: lista os destinatários e grava o log de envio.
/// O worker NUNCA fala com o MySQL — a fonte de verdade continua sendo a api,
/// exatamente como o scraper faz desde a Sprint 3.
/// </summary>
public sealed class ClientePonteApi(
    HttpClient http,
    IOptions<OpcoesNewsletter> opcoes,
    ILogger<ClientePonteApi> log) : IClientePonteApi
{
    private readonly OpcoesNewsletter _opcoes = opcoes.Value;
    private string? _token;

    private async Task<string> TokenAsync(CancellationToken cancelamento)
    {
        if (_token is not null)
        {
            return _token;
        }

        var resposta = await http.PostAsJsonAsync(
            "/api/auth/login",
            new { email = _opcoes.ApiEmail, senha = _opcoes.ApiSenha },
            cancelamento);
        resposta.EnsureSuccessStatusCode();

        using var corpo = JsonDocument.Parse(
            await resposta.Content.ReadAsStringAsync(cancelamento));
        _token = corpo.RootElement.GetProperty("access_token").GetString()
            ?? throw new InvalidOperationException("login sem access_token");
        return _token;
    }

    private async Task<HttpRequestMessage> AutenticadaAsync(
        HttpMethod metodo, string caminho, CancellationToken cancelamento)
    {
        var pedido = new HttpRequestMessage(metodo, caminho);
        pedido.Headers.Authorization =
            new AuthenticationHeaderValue("Bearer", await TokenAsync(cancelamento));
        return pedido;
    }

    public async Task<IReadOnlyList<string>> InscritosAtivosAsync(CancellationToken cancelamento)
    {
        using var pedido = await AutenticadaAsync(
            HttpMethod.Get, "/api/newsletter/inscritos", cancelamento);
        using var resposta = await http.SendAsync(pedido, cancelamento);
        resposta.EnsureSuccessStatusCode();
        return await resposta.Content.ReadFromJsonAsync<List<string>>(cancelamento) ?? [];
    }

    public async Task MarcarEnviadaAsync(DateOnly data, CancellationToken cancelamento)
    {
        var caminho = $"/api/newsletter/edicoes/{data:yyyy-MM-dd}/enviada";
        using var pedido = await AutenticadaAsync(HttpMethod.Post, caminho, cancelamento);
        using var resposta = await http.SendAsync(pedido, cancelamento);
        if (!resposta.IsSuccessStatusCode)
        {
            log.LogWarning(
                "não foi possível marcar a edição {Data} como enviada: {Status}",
                data,
                resposta.StatusCode);
            return;
        }

        log.LogInformation("edição {Data} marcada como enviada", data);
    }
}

/// <summary>Assunto do e-mail — função pura, fácil de testar.</summary>
public static class AssuntoEdicao
{
    public static string Para(Edicao edicao) =>
        $"Ponte Italia · {edicao.Data:dd/MM/yyyy} · {edicao.Total} destaque(s) para sua jornada";
}
