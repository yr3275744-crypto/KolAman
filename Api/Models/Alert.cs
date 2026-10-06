using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using System.Text.Json.Serialization;

namespace Api.Models
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
        public string Priority { get; set; } = string.Empty;

        [JsonPropertyName("classification")]
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

        public string Headquarter { get; set; } = string.Empty;
    }
}
