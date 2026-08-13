# Worker .NET da newsletter — build multi-stage (SDK compila, runtime executa).
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build

WORKDIR /src
COPY Newsletter.sln ./
COPY Newsletter.Worker/Newsletter.Worker.csproj ./Newsletter.Worker/
COPY Newsletter.Tests/Newsletter.Tests.csproj ./Newsletter.Tests/
RUN dotnet restore Newsletter.Worker/Newsletter.Worker.csproj

COPY Newsletter.Worker ./Newsletter.Worker
RUN dotnet publish Newsletter.Worker/Newsletter.Worker.csproj \
    -c Release -o /app/publish --no-restore

FROM mcr.microsoft.com/dotnet/runtime:8.0 AS runtime

WORKDIR /app
COPY --from=build /app/publish ./

# o RazorLight compila o .cshtml em runtime — o template acompanha o publish
ENV DOTNET_EnableDiagnostics=0

RUN useradd --create-home --uid 10003 ponte && chown -R ponte:ponte /app
USER ponte

ENTRYPOINT ["dotnet", "Newsletter.Worker.dll"]
