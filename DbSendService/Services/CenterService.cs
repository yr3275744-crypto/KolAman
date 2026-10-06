using DbSendService.DAL;
using DbSendService.Loggers;
using DbSendService.Models;
using Microsoft.Extensions.Hosting;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DbSendService.Services
{
    public class CenterService : BackgroundService
    {
        private readonly IConnection _rabbitConnection;
        private readonly ICastomLogger _logger;
        private readonly MongoClient _mongoClient;
        private readonly ConfigStrings _configStrings;
        public CenterService(IConnection connection,
            ICastomLogger logger,
            MongoClient mongoClient,
            ConfigStrings configStrings)
        {
            _rabbitConnection = connection;
            _logger = logger;
            _mongoClient = mongoClient;
            _configStrings = configStrings;
        }
        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {

            while (!stoppingToken.IsCancellationRequested)
            {
                using var channel = await _rabbitConnection.CreateChannelAsync();
                await channel.QueueDeclareAsync(queue: _configStrings.CenterQueuName, durable: true, exclusive: false, autoDelete: false,
                    arguments: null);
                Console.WriteLine("Center Waiting for messages.");

                var consumer = new AsyncEventingBasicConsumer(channel);
                consumer.ReceivedAsync += (model, ea) =>
                {
                    var body = ea.Body.ToArray();
                    var message = Encoding.UTF8.GetString(body);
                    Console.WriteLine($"Center Received {message}");
                    return Task.CompletedTask;
                };

                await channel.BasicConsumeAsync(_configStrings.CenterQueuName, autoAck: true, consumer: consumer);

                Console.WriteLine(" Press [enter] to exit.");
                Console.ReadLine();
            }
        }
    }
}
