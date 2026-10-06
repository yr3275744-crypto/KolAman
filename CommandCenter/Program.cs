using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.DependencyInjection;
using CommandCenter.Services;
using CommandCenter.Models;
using CommandCenter.DAL;

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

builder.Services.AddHostedService<TaskManager>();
builder.Services.AddSingleton<ConfigStrings>();
builder.Services.AddSingleton<MongoClientAccess>();

using IHost host = builder.Build();

host.Run();