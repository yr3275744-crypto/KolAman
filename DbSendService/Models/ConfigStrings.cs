using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace DbSendService.Models
{
    public class ConfigStrings
    {
        public string NorthQueuName { get; set; } = "NORTH";
        public string DepthQueuName { get; set; } = "DEPTH";
        public string SouthQueuName { get; set; } = "SOUTH";
        public string CenterQueuName { get; set; } = "CENTER";
        public string ConnectionString { get; set; } = "mongodb://localhost:27017";
        public string DatabaseName { get; set; } = "Alerts";
        public string AlertsCollectionName { get; set; } = "AllAlerts";
    }
}
