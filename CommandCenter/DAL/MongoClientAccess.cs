using CommandCenter.Enums;
using CommandCenter.Models;
using MongoDB.Driver;
using MongoDB.Driver.Linq;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CommandCenter.DAL
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
        public async Task<List<Alert>> GetNewAlerts()
        {
            var result = await AllAlertsCollection.AsQueryable().Where(a => a.Status == "WAITING").ToListAsync();
            return result;
        }
        public async Task SetStatus(Alert alert,StatusLevel statusLevel)
        {
            Alert newAlert = new Alert
            {
                Status = statusLevel.ToString(),
                Id = alert.Id,
                AlertId = alert.AlertId,
                Classification = alert.Classification,
                Content = alert.Content,
                DetectedAt = alert.DetectedAt,
                Headquarter = alert.Headquarter,
                Lat = alert.Lat,
                Lon = alert.Lon,
                Priority = alert.Priority,
                Source = alert.Source,
                TimeStamp = alert.TimeStamp,
                Title = alert.Title
            };
            Console.WriteLine($"new status: {newAlert.Status}");
            await AllAlertsCollection.ReplaceOneAsync(a => a.Id == newAlert.Id, newAlert);
        }
    }
}
