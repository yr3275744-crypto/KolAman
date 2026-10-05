using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NotificationGate.Models
{
    public class ConfigStrings
    {
        public string BootstrapServers { get; set; } = string.Empty;
        public string NotificationGetTopik { get; set; } = string.Empty;
        public string WatchPath { get; set; } = string.Empty;
    }
}
