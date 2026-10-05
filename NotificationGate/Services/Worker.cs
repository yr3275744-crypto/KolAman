using Microsoft.Extensions.Hosting;
using NotificationGate.Models;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NotificationGate.Services
{
    public class Worker : BackgroundService
    {
        private readonly NotificationsSender _filesWatcher;
        private readonly ConfigStrings _configStrings;
        public Worker(NotificationsSender filesWatcher,
            ConfigStrings configStrings)
        {
            _filesWatcher = filesWatcher;
            _configStrings = configStrings;
        }
        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            try
            {
                Console.WriteLine(_configStrings.WatchPath);
                while (!stoppingToken.IsCancellationRequested)
                {
                    await _filesWatcher.Watch(_configStrings.WatchPath);
                }
            }
            catch (System.ArgumentException ex)
            {
                Console.WriteLine(ex);
            }
        }
    }
}
