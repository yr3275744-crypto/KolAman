using Api.DAL;
using Api.Models;
using Api.Models.Dtos;
using Microsoft.AspNetCore.Mvc;
using MongoDB.Driver;
using MongoDB.Driver.Linq;

namespace Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AlertsController : ControllerBase
    {
        private readonly MongoClientAccess _mongoClient;
        public AlertsController(MongoClientAccess mongoClientAccess)
        {
            _mongoClient = mongoClientAccess;
        }

        [HttpGet]
        public async Task<ActionResult<IEnumerable<Alert>>> GetAll()
        {
            var result = await _mongoClient.GetAlerts();
            return Ok(result);
        }

        [HttpGet("count-by-group")]
        public async Task<ActionResult<IEnumerable<CountByCommandDto>>> CountByCommand()
        {
            var result = await _mongoClient.AllAlertsCollection.AsQueryable()
                .GroupBy(a => a.Headquarter)
                .Select(g => new CountByCommandDto
                {
                    Group = g.Key,
                    Count = g.Count()
                })
                .ToListAsync();
            return Ok(result);
        }
    }
}
