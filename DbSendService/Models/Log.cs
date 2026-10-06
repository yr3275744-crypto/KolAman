using DbSendService.Enums;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace DbSendService.Models
{
    public class Log
    {
        [JsonConverter(typeof(JsonStringEnumConverter))]
        public LogsLevelValues Level { get; set; }
        
        public string Message { get; set; } = string.Empty;

        [JsonPropertyName("@timestamp")]
        public DateTime Timestamp { get; set; }


        [JsonConverter(typeof(JsonStringEnumConverter))]
        public RelevantHeadquartersValues RelevantHeadquarters { get; set; }
    }
}
