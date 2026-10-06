using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace CommandCenter.Models
{
    public class ConfigStrings
    {
        public string ConnectionString { get; set; } = "mongodb://localhost:27017";
        public string DatabaseName { get; set; } = "Alerts";
        public string AlertsCollectionName { get; set; } = "AllAlerts";
    }
}
