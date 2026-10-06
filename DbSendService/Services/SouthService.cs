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
    public class SouthService : BackgroundService
    {
        private readonly IConnection _rabbitConnection;
        private readonly ICastomLogger _logger;
        private readonly MongoClient _mongoClient;
        private readonly ConfigStrings _configStrings;
        public SouthService(IConnection connection,
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
                await channel.QueueDeclareAsync(queue: _configStrings.SouthQueuName, durable: true, exclusive: false, autoDelete: false,
                    arguments: null);
                Console.WriteLine("South Waiting for messages.");

                var consumer = new AsyncEventingBasicConsumer(channel);
                consumer.ReceivedAsync += (model, ea) =>
                {
                    var body = ea.Body.ToArray();
                    var message = Encoding.UTF8.GetString(body);
                    Console.WriteLine($"South Received {message}");
                    return Task.CompletedTask;
                };

                await channel.BasicConsumeAsync(_configStrings.SouthQueuName, autoAck: true, consumer: consumer);

                Console.WriteLine(" Press [enter] to exit.");
                Console.ReadLine();
            }
        }
    }
}
