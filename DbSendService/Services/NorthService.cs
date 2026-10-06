using DbSendService.DAL;
using DbSendService.Loggers;
using RabbitMQ.Client;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DbSendService.Services
{
    public class NorthService
    {
        private readonly IConnection _rabbitConnection;
        private readonly ICastomLogger _logger;
        private readonly MongoClient _mongoClient;
        public NorthService(IConnection connection,
            ICastomLogger logger,
            MongoClient mongoClient)
        {
            _rabbitConnection = connection;
            _logger = logger;
            _mongoClient = mongoClient;
        }
    }
}
