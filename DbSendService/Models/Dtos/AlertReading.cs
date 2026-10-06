using DbSendService.Enums;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json.Serialization;
using System.Threading.Tasks;

namespace DbSendService.Models.Dtos
{
    public class AlertReading
    {
        public string AlertId { get; set; } = string.Empty;

        [JsonPropertyName("source")]
        public string Source { get; set; } = string.Empty;

        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("content")]
        public string Content { get; set; } = string.Empty;

        [JsonPropertyName("priority")]
        public string? Priority { get; set; }

        [JsonPropertyName("classification")]
        public string? Classification { get; set; }

        [JsonPropertyName("lat")]
        public int? Lat { get; set; }

        [JsonPropertyName("lon")]
        public int? Lon { get; set; }

        [JsonPropertyName("timestamp")]
        public DateTime? TimeStamp { get; set; }

        [JsonPropertyName("status")]
        public string? Status { get; set; }

    }
}
