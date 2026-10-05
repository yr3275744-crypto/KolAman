using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using NotificationGate.DAL;
using NotificationGate.Models;
using NotificationGate.Services;

DotNetEnv.Env.Load();



HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

string watchPath = builder.Environment.ContentRootPath +@Environment.GetEnvironmentVariable("WATCH_PATH")!;

builder.Services.AddHostedService<Worker>();
builder.Services.AddSingleton(sp => new ConfigStrings
{
    BootstrapServers = Environment.GetEnvironmentVariable("KAFKA_BOOTSTRAP_SERVERS")!,
    NotificationGetTopik = Environment.GetEnvironmentVariable("NOTIFICATION_GET_TOPIK")!,
    WatchPath = Path.Combine(builder.Environment.ContentRootPath, Environment.GetEnvironmentVariable("WATCH_PATH")!)
});
builder.Services.AddSingleton<kafkaClient>();
builder.Services.AddSingleton<FilesWatcher>();

using IHost host = builder.Build();

host.Run();