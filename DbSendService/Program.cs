using DbSendService.DAL;
using DbSendService.Loggers;
using DbSendService.Models;
using DbSendService.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using RabbitMQ.Client;

//defin rabbit connection
var factory = new ConnectionFactory { HostName = "localhost" };
IConnection rabbitConnection = await factory.CreateConnectionAsync();

//the host and services definition

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

//builder.Services.AddHostedService<Worker>();
builder.Services.AddHostedService<CenterService>();
builder.Services.AddHostedService<DepthService>();
builder.Services.AddHostedService<NorthService>();
builder.Services.AddHostedService<SouthService>();
builder.Services.AddSingleton(sp => new ConfigStrings());
builder.Services.AddSingleton<ICastomLogger,ElasticLogger>();
builder.Services.AddSingleton(sp => rabbitConnection);
builder.Services.AddSingleton<MongoClientAccess>();
builder.Services.AddSingleton<AlertProccessor>();

using IHost host = builder.Build();

host.Run();
