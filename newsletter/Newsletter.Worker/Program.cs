using Microsoft.Extensions.Options;
using Newsletter.Worker.Configuracao;
using Newsletter.Worker.Jobs;
using Newsletter.Worker.Servicos;
using Quartz;
using StackExchange.Redis;

var builder = Host.CreateApplicationBuilder(args);

// as mesmas variáveis do .env do compose (MYSQL_*, REDIS_*, SMTP_*, PONTE_*)
builder.Services
    .AddOptions<OpcoesNewsletter>()
    .Bind(builder.Configuration.GetSection(OpcoesNewsletter.Secao))
    .Configure(opcoes =>
    {
        var ambiente = builder.Configuration;
        opcoes.RedisHost = ambiente["REDIS_HOST"] ?? opcoes.RedisHost;
        opcoes.RedisPort = int.TryParse(ambiente["REDIS_PORT"], out var porta)
            ? porta
            : opcoes.RedisPort;
        opcoes.SmtpHost = ambiente["SMTP_HOST"] ?? opcoes.SmtpHost;
        opcoes.SmtpPort = int.TryParse(ambiente["SMTP_PORT"], out var smtp)
            ? smtp
            : opcoes.SmtpPort;
        opcoes.SmtpUsuario = ambiente["SMTP_USER"] ?? opcoes.SmtpUsuario;
        opcoes.SmtpSenha = ambiente["SMTP_PASSWORD"] ?? opcoes.SmtpSenha;
        opcoes.SmtpUsarTls = bool.TryParse(ambiente["SMTP_USAR_TLS"], out var tls) && tls;
        opcoes.Remetente = ambiente["NEWSLETTER_FROM"] ?? opcoes.Remetente;
        opcoes.ApiUrl = ambiente["PONTE_API"] ?? opcoes.ApiUrl;
        opcoes.ApiEmail = ambiente["PONTE_EMAIL"] ?? opcoes.ApiEmail;
        opcoes.ApiSenha = ambiente["PONTE_SENHA"] ?? opcoes.ApiSenha;
    });

builder.Services.AddSingleton<IConnectionMultiplexer>(provedor =>
{
    var opcoes = provedor.GetRequiredService<IOptions<OpcoesNewsletter>>().Value;
    return ConnectionMultiplexer.Connect($"{opcoes.RedisHost}:{opcoes.RedisPort}");
});

builder.Services.AddSingleton<IFilaEdicoes, FilaRedis>();
builder.Services.AddSingleton<IRenderizadorEdicao, RenderizadorRazor>();
builder.Services.AddSingleton<IEnviadorEmail, EnviadorMailKit>();
builder.Services.AddHttpClient<IClientePonteApi, ClientePonteApi>((provedor, http) =>
{
    var opcoes = provedor.GetRequiredService<IOptions<OpcoesNewsletter>>().Value;
    http.BaseAddress = new Uri(opcoes.ApiUrl);
});

builder.Services.AddQuartz(quartz =>
{
    var opcoes = builder.Configuration
        .GetSection(OpcoesNewsletter.Secao)
        .Get<OpcoesNewsletter>() ?? new OpcoesNewsletter();
    var chave = new JobKey("disparo-newsletter");

    quartz.AddJob<DisparoDiarioJob>(job => job.WithIdentity(chave));
    quartz.AddTrigger(gatilho => gatilho
        .ForJob(chave)
        .WithIdentity("disparo-newsletter-09h")
        .WithCronSchedule(
            opcoes.Cron,
            cron => cron.InTimeZone(TimeZoneInfo.FindSystemTimeZoneById(opcoes.FusoHorario))));
});
builder.Services.AddQuartzHostedService(quartz => quartz.WaitForJobsToComplete = true);

var host = builder.Build();
host.Run();
