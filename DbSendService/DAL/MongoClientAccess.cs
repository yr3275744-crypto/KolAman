using DbSendService.Enums;
using DbSendService.Models;
using DbSendService.Models.Dtos;
using MongoDB.Driver;
using MongoDB.Driver.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DbSendService.DAL
{
    public class MongoClientAccess
    {
        private ConfigStrings _configStrings;
        public IMongoCollection<Alert> AllAlertsCollection { get; set; }
        public MongoClientAccess(ConfigStrings configStrings)
        {
            _configStrings = configStrings;
            MongoClient mongoClient = new MongoClient(_configStrings.ConnectionString);
            var mongoDatabase = mongoClient.GetDatabase(_configStrings.DatabaseName);
            AllAlertsCollection = mongoDatabase.GetCollection<Alert>(_configStrings.AlertsCollectionName);
        }
        public async Task Send(AlertReading reading,
            RelevantHeadquartersValues headquarter)
        {
            try
            {
                await AllAlertsCollection.InsertOneAsync(new Alert
                {
                    AlertId = reading.AlertId,
                    Content = reading.Content,
                    Classification = Enum.Parse<ClassificationLevel>(reading.Classification, false),
                    DetectedAt = DateTime.UtcNow,
                    Headquarter = headquarter.ToString(),
                    //Lat = double.Parse(reading.Lat),
                    //Lon = double.Parse(reading.Lon),
                    Lat = (double)reading.Lat,
                    Lon = (double)reading.Lon,
                    Priority = Enum.Parse<PriorityLevel>(reading.Priority),
                    Source = reading.Source,
                    Status = Enum.Parse<StatusLevel>(reading.Status),
                    TimeStamp = (DateTime)reading.TimeStamp,
                    Title = reading.Title
                });
            }
            catch (Exception e)
            {
                Console.WriteLine(e);
            }
        }
        public async Task TryJust()
        {
            //await AllAlertsCollection.InsertOneAsync(new Alert());
            var r = await AllAlertsCollection.AsQueryable().Where(a => a.AlertId == "").ToListAsync();
            foreach (var d in r)
            {
                Console.WriteLine(d.AlertId);
            }
        }
    }
}
