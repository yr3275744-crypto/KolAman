using DbSendService.DAL;
using DbSendService.Enums;
using DbSendService.Models;
using DbSendService.Models.Dtos;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace DbSendService.Services
{
    public class AlertProccessor
    {
        private readonly MongoClientAccess _clientAccess;
        public AlertProccessor(MongoClientAccess mongoClientAccess)
        {
            _clientAccess = mongoClientAccess;
        }
        public async Task Proccess(string message, RelevantHeadquartersValues headquarter)
        {
            try
            {
                AlertReading? reading = JsonSerializer.Deserialize<AlertReading>(message);
            //}
            //catch (Exception e)
            //{
            //    Console.WriteLine(e.Message);
            //}
            //AlertReading? reading = JsonSerializer.Deserialize<AlertReading>(message);
            if (reading == null)
            {
                Console.WriteLine("fail to serialize alert");
                return;
            }
            //try
            //{
                await _clientAccess.Send(reading, headquarter);
            }
            catch (Exception e)
            {
                Console.WriteLine($"fail to send to mongo: {e}");
            }
        }
    }
}
