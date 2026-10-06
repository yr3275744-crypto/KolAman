using Api.Models;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Api.DAL
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
        public async Task<List<Alert>> GetAlerts()
        {
            var result = await AllAlertsCollection.AsQueryable().ToListAsync();
            return result;
        }
    }
}
