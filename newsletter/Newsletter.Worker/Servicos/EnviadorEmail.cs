using MailKit.Net.Smtp;
using MailKit.Security;
using Microsoft.Extensions.Options;
using MimeKit;
using Newsletter.Worker.Configuracao;

namespace Newsletter.Worker.Servicos;

public interface IEnviadorEmail
{
    /// <summary>Content-ID do logo embutido; o template o referencia por `cid:`.</summary>
    const string ContentIdLogo = "logo-ponte-italia";

    Task EnviarAsync(
        IReadOnlyCollection<string> destinatarios,
        string assunto,
        string html,
        CancellationToken cancelamento);
}

/// <summary>
/// Envio por SMTP via MailKit. Em dev o host é o Mailpit do docker-compose, que
/// CAPTURA as mensagens em vez de entregá-las — nenhum e-mail real sai daqui.
/// Nos testes, esta classe é substituída pela interface (nada de rede).
/// </summary>
public sealed class EnviadorMailKit(
    IOptions<OpcoesNewsletter> opcoes,
    ILogger<EnviadorMailKit> log) : IEnviadorEmail
{
    private readonly OpcoesNewsletter _opcoes = opcoes.Value;

    public async Task EnviarAsync(
        IReadOnlyCollection<string> destinatarios,
        string assunto,
        string html,
        CancellationToken cancelamento)
    {
        if (destinatarios.Count == 0)
        {
            log.LogInformation("nenhum inscrito ativo — nada a enviar");
            return;
        }

        using var cliente = new SmtpClient();
        var seguranca = _opcoes.SmtpUsarTls
            ? SecureSocketOptions.StartTls
            : SecureSocketOptions.None;
        await cliente.ConnectAsync(_opcoes.SmtpHost, _opcoes.SmtpPort, seguranca, cancelamento);

        if (!string.IsNullOrEmpty(_opcoes.SmtpUsuario))
        {
            await cliente.AuthenticateAsync(_opcoes.SmtpUsuario, _opcoes.SmtpSenha, cancelamento);
        }

        var logo = Path.Combine(AppContext.BaseDirectory, "Recursos", "logo-marca.png");

        // uma mensagem por inscrito: cada um em Bcc vazaria a lista de e-mails
        foreach (var destinatario in destinatarios)
        {
            var corpo = new BodyBuilder { HtmlBody = html };
            if (File.Exists(logo))
            {
                // recurso vinculado (cid:) — o Gmail bloqueia imagem em data: URI
                var recurso = corpo.LinkedResources.Add(logo);
                recurso.ContentId = IEnviadorEmail.ContentIdLogo;
            }

            var mensagem = new MimeMessage
            {
                Subject = assunto,
                Body = corpo.ToMessageBody(),
            };
            mensagem.From.Add(new MailboxAddress(_opcoes.NomeRemetente, _opcoes.Remetente));
            mensagem.To.Add(MailboxAddress.Parse(destinatario));
            await cliente.SendAsync(mensagem, cancelamento);
        }

        await cliente.DisconnectAsync(quit: true, cancelamento);
        log.LogInformation("{Total} e-mail(s) enviados via {Host}", destinatarios.Count, _opcoes.SmtpHost);
    }
}
