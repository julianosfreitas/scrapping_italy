using System.Text.Json;
using Microsoft.Extensions.Options;
using Newsletter.Worker.Configuracao;
using Newsletter.Worker.Modelos;
using StackExchange.Redis;

namespace Newsletter.Worker.Servicos;

public interface IFilaEdicoes
{
    /// <summary>Retira a próxima edição da fila, ou null se não houver nenhuma.</summary>
    Task<Edicao?> ProximaAsync(CancellationToken cancelamento);
}

/// <summary>
/// Consumidor da lista Redis alimentada por <c>app/core/fila.py</c>.
/// O Python faz LPUSH; aqui fazemos RPOP — a ponta oposta, o que dá FIFO.
/// </summary>
public sealed class FilaRedis(
    IConnectionMultiplexer conexao,
    IOptions<OpcoesNewsletter> opcoes,
    ILogger<FilaRedis> log) : IFilaEdicoes
{
    private readonly OpcoesNewsletter _opcoes = opcoes.Value;

    /// <summary>
    /// Desserialização isolada em método estático: é a parte testável do
    /// consumo da fila, e não precisa de Redis nenhum para ser exercitada.
    /// </summary>
    public static Edicao? Desserializar(string? json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return null;
        }

        try
        {
            return JsonSerializer.Deserialize<Edicao>(json);
        }
        catch (JsonException)
        {
            return null;
        }
    }

    public async Task<Edicao?> ProximaAsync(CancellationToken cancelamento)
    {
        cancelamento.ThrowIfCancellationRequested();
        var bruto = await conexao.GetDatabase().ListRightPopAsync(_opcoes.Fila);
        if (bruto.IsNullOrEmpty)
        {
            return null;
        }

        var edicao = Desserializar(bruto.ToString());
        if (edicao is null)
        {
            log.LogWarning("payload inválido descartado da fila {Fila}", _opcoes.Fila);
        }

        return edicao;
    }
}
