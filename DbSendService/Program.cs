using DbSendService.Services;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using RabbitMQ.Client;

//defin rabbit connection
var factory = new ConnectionFactory { HostName = "localhost" };
IConnection rabbitConnection = await factory.CreateConnectionAsync();

//the host and services definition

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

builder.Services.AddHostedService<Worker>();