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
        private readonly MongoClientAccess _mongoClient;
        private readonly ConfigStrings _configStrings;
        private readonly AlertProccessor _alertProccessor;
        public SouthService(IConnection connection,
            ICastomLogger logger,
            MongoClientAccess mongoClient,
            ConfigStrings configStrings,
            AlertProccessor alertProccessor)
        {
            _rabbitConnection = connection;
            _logger = logger;
            _mongoClient = mongoClient;
            _configStrings = configStrings;
            _alertProccessor = alertProccessor;
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
                consumer.ReceivedAsync += async (model, ea) =>
                {
                    try
                    {
                        var body = ea.Body.ToArray();
                        var message = Encoding.UTF8.GetString(body);
                        Console.WriteLine($"Center Received {message}");
                        await _alertProccessor.Proccess(message, Enums.RelevantHeadquartersValues.SOUTH);
                        await channel.BasicAckAsync(deliveryTag: ea.DeliveryTag, multiple: false);
                    }
                    catch (Exception e)
                    {
                        Console.WriteLine(e);
                    }
                };

                await channel.BasicConsumeAsync(_configStrings.SouthQueuName, autoAck: false, consumer: consumer);

                Console.WriteLine(" Press [enter] to exit.");
                Console.ReadLine();
            }
        }
    }
}
