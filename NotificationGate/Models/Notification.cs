using NotificationGate.Enums;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace NotificationGate.Models
{
    public class Notification
    {
        [JsonPropertyName("alert_id")]
        public string AlertId { get; set; } = string.Empty;

        [JsonPropertyName("source")]
        public string Source { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        [JsonConverter(typeof(JsonStringEnumConverter))]
        public PriorityLevel Priority { get; set; }

        [JsonPropertyName("classification")]
        [JsonConverter(typeof(JsonStringEnumConverter))]
        public ClassificationLevel Classification { get; set; }

        [JsonPropertyName("lat")]
        public int? Lat { get; set; }

        [JsonPropertyName("lon")]
        public int? Lon { get; set; }

        [JsonPropertyName("timestamp")]
        public DateTime? TimeStamp { get; set; }

        [JsonPropertyName("status")]
        [JsonConverter(typeof(JsonStringEnumConverter))]
        public StatusLevel Status { get; set; }
    }
}
