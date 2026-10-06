namespace Api.Models
{
    public class ConfigStrings
    {
        public string ConnectionString { get; set; } = "mongodb://localhost:27017";
        public string DatabaseName { get; set; } = "Alerts";
        public string AlertsCollectionName { get; set; } = "AllAlerts";
    }
}
