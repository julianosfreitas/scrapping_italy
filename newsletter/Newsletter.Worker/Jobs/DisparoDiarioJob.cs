using Newsletter.Worker.Servicos;
using Quartz;

namespace Newsletter.Worker.Jobs;

/// <summary>
/// Job das 09h (Quartz, fuso America/Recife): drena a fila do Redis e dispara
/// cada edição pendente. `DisallowConcurrentExecution` evita que uma execução
/// atrasada se sobreponha à seguinte e envie o mesmo e-mail duas vezes.
/// </summary>
[DisallowConcurrentExecution]
public sealed class DisparoDiarioJob(
    IFilaEdicoes fila,
    IRenderizadorEdicao renderizador,
    IEnviadorEmail enviador,
    IClientePonteApi api,
    ILogger<DisparoDiarioJob> log) : IJob
{
    public async Task Execute(IJobExecutionContext contexto)
    {
        var cancelamento = contexto.CancellationToken;
        var enviadas = 0;

        while (await fila.ProximaAsync(cancelamento) is { } edicao)
        {
            var destinatarios = await api.InscritosAtivosAsync(cancelamento);
            var html = await renderizador.RenderizarAsync(edicao);
            await enviador.EnviarAsync(
                destinatarios, AssuntoEdicao.Para(edicao), html, cancelamento);
            await api.MarcarEnviadaAsync(edicao.Data, cancelamento);
            enviadas++;
        }

        if (enviadas == 0)
        {
            log.LogInformation("fila vazia — nenhuma edição para disparar");
            return;
        }

        log.LogInformation("{Total} edição(ões) disparada(s)", enviadas);
    }
}
