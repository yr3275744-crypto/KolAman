using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CommandCenter.DAL;
using CommandCenter.Enums;
using CommandCenter.Models;
using Microsoft.Extensions.Hosting;

namespace CommandCenter.Services
{
    public class TaskManager : BackgroundService
    {
        private readonly MongoClientAccess _mongoClientAccess;
        private readonly Random _rand;
        public TaskManager(MongoClientAccess mongoClientAccess)
        {
            _mongoClientAccess = mongoClientAccess;
            _rand = new Random();
        }
        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            while (!stoppingToken.IsCancellationRequested)
            {
                var newAlerts = await _mongoClientAccess.GetNewAlerts();
                foreach (Alert alert in newAlerts)
                {
                    PriorityLevel priorityLevel;
                    var pPars = Enum.TryParse<PriorityLevel>(alert.Priority, false, out priorityLevel);
                    if (pPars == false)
                    {
                        Console.WriteLine("invalid priority in the alert. pleas check");
                        continue;
                    }
                    if (alert.Priority == PriorityLevel.LOW.ToString())
                    {
                        await _mongoClientAccess.SetStatus(alert, StatusLevel.CANCEL);
                        continue;
                    }
                    
                    int randomInt = _rand.Next(0, 3000);
                    await _mongoClientAccess.SetStatus(alert, StatusLevel.INPROGRESS);
                    await Task.Delay(randomInt);
                    await _mongoClientAccess.SetStatus(alert, StatusLevel.DONE);
                    Console.WriteLine($"Time of proccess: {randomInt}");
                }
            }
        }
    }
}