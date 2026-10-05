using Confluent.Kafka;
using NotificationGate.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NotificationGate.DAL
{
    public class kafkaClient
    {
        public IProducer<Null, string> Producer { get; set; }
        public kafkaClient(ConfigStrings configStrings)
        {
            var config = new ProducerConfig
            {
                BootstrapServers = configStrings.BootstrapServers
            };
            Producer = new ProducerBuilder<Null, string>(config).Build();
        }
    }
}
