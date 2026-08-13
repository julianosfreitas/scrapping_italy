using Newsletter.Worker.Modelos;
using RazorLight;

namespace Newsletter.Worker.Servicos;

public interface IRenderizadorEdicao
{
    Task<string> RenderizarAsync(Edicao edicao);
}

/// <summary>
/// Renderiza o HTML do e-mail com Razor (RazorLight compila o .cshtml em runtime).
/// O template mora em Templates/Edicao.cshtml e segue a identidade da seção 8 do
/// README — fundo off-white, grafite no texto, um verde de ação.
/// </summary>
public sealed class RenderizadorRazor : IRenderizadorEdicao
{
    private const string Chave = "Edicao";
    private readonly RazorLightEngine _engine;

    public RenderizadorRazor()
    {
        var raiz = Path.Combine(AppContext.BaseDirectory, "Templates");
        _engine = new RazorLightEngineBuilder()
            // sem isto o RazorLight procura as referências no assembly de ENTRADA,
            // que sob o test host não conhece os modelos do worker
            .SetOperatingAssembly(typeof(Edicao).Assembly)
            .UseFileSystemProject(raiz)
            .UseMemoryCachingProvider()
            .Build();
    }

    public Task<string> RenderizarAsync(Edicao edicao) =>
        _engine.CompileRenderAsync($"{Chave}.cshtml", edicao);
}
