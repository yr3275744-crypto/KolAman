using CommandCenter.Enums;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace CommandCenter.Models
{
    public class Alert
    {
        [BsonId]
        [BsonRepresentation(BsonType.ObjectId)]
        public string? Id { get; set; }
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
        public string Priority { get; set; } = string.Empty;

        [JsonPropertyName("classification")]
        [JsonConverter(typeof(JsonStringEnumConverter))]
        public string Classification { get; set; } = string.Empty;

        [JsonPropertyName("lat")]
        public double Lat { get; set; }

        [JsonPropertyName("lon")]
        public double Lon { get; set; }

        [JsonPropertyName("timestamp")]
        public DateTime TimeStamp { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;

        public DateTime DetectedAt { get; set; }

        [JsonConverter(typeof(JsonStringEnumConverter))]
        public string Headquarter { get; set; } = string.Empty;
    }
}
