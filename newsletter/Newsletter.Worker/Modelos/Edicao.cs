using System.Text.Json.Serialization;

namespace Newsletter.Worker.Modelos;

/// <summary>
/// Contrato da edição publicada pela curadoria em Python (app/schemas/newsletter.py).
/// As chaves são snake_case porque é assim que o Pydantic serializa; mapear aqui,
/// e não renomear do outro lado, mantém a API REST idiomática em Python.
/// </summary>
public sealed record Edicao
{
    [JsonPropertyName("data")]
    public required DateOnly Data { get; init; }

    [JsonPropertyName("gerada_em")]
    public required DateTime GeradaEm { get; init; }

    [JsonPropertyName("total")]
    public required int Total { get; init; }

    [JsonPropertyName("topicos")]
    public required IReadOnlyList<TopicoEdicao> Topicos { get; init; }
}

public sealed record TopicoEdicao
{
    [JsonPropertyName("chave")]
    public required string Chave { get; init; }

    [JsonPropertyName("rotulo")]
    public required string Rotulo { get; init; }

    [JsonPropertyName("itens")]
    public required IReadOnlyList<ItemEdicao> Itens { get; init; }
}

public sealed record ItemEdicao
{
    [JsonPropertyName("titulo")]
    public required string Titulo { get; init; }

    [JsonPropertyName("url")]
    public required string Url { get; init; }

    [JsonPropertyName("fonte")]
    public required string Fonte { get; init; }

    [JsonPropertyName("resumo")]
    public string? Resumo { get; init; }

    [JsonPropertyName("publicada_em")]
    public DateTime? PublicadaEm { get; init; }
}
