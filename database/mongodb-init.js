db = db.getSiblingDB("dns_monitor");

db.createUser({
  user: "dnsapp",
  pwd: "dnsapp-local-only",
  roles: [{ role: "readWrite", db: "dns_monitor" }],
});