namespace Newsletter.Worker.Configuracao;

/// <summary>
/// Configuração do worker. Os valores chegam por variável de ambiente (o mesmo
/// .env do compose) ou por appsettings.json — nada de segredo no repositório.
/// </summary>
public sealed class OpcoesNewsletter
{
    public const string Secao = "Newsletter";

    // Redis (fila publicada pela curadoria em Python)
    public string RedisHost { get; set; } = "localhost";
    public int RedisPort { get; set; } = 6379;
    public string Fila { get; set; } = "newsletter:fila";

    // SMTP — em dev aponta para o Mailpit do docker-compose (porta 1025)
    public string SmtpHost { get; set; } = "localhost";
    public int SmtpPort { get; set; } = 1025;
    public string SmtpUsuario { get; set; } = "";
    public string SmtpSenha { get; set; } = "";
    public bool SmtpUsarTls { get; set; }
    public string Remetente { get; set; } = "newsletter@ponteitalia.example";
    public string NomeRemetente { get; set; } = "Ponte Italia";

    // API do site: lista de inscritos e log de envio
    public string ApiUrl { get; set; } = "http://localhost:8000";
    public string ApiEmail { get; set; } = "";
    public string ApiSenha { get; set; } = "";

    /// <summary>Cron do disparo: 09h todos os dias (seção 7 do README).</summary>
    public string Cron { get; set; } = "0 0 9 * * ?";

    public string FusoHorario { get; set; } = "America/Recife";

    /// <summary>
    /// Drena a fila uma vez logo na subida, além do cron — mesmo comportamento
    /// do scraper ("primeira execução imediata"). Usado na demo e em operação
    /// manual; em produção fica desligado.
    /// </summary>
    public bool DispararAoIniciar { get; set; }
}
