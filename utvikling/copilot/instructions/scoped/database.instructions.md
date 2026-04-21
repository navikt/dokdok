---
applyTo: "**/*Repository*.java,**/db/migration/**,**/*.sql"
---

# Database Conventions

- PK names: full table name (without prefix) + `id` (`t_dokument_info` -> `dokument_info_id`)
- Replace Norwegian letters in DB names: `æ->e`, `ø->o`, `å->a`
- `VARCHAR2` sizes: `128`, `512`, `4000` char; use `CLOB` above `4000`
- Use `DATE` by default, `TIMESTAMP` only when needed

## Java-to-Oracle Type Mapping

| JAVA TYPE | ORACLE DATABASE TYPE |
|-----------|--------------------------|
| boolean, java.lang.Boolean | NUMBER(1) |
| int, java.lang.Integer | NUMBER(10) |
| long, java.lang.Long | NUMBER(19) |
| float, java.lang.Float | NUMBER(19,4) |
| double, java.lang.Double | NUMBER(19,4) |
| short, java.lang.Short | NUMBER(5) |
| byte, java.lang.Byte | NUMBER(3) |
| enums, java.lang.String | VARCHAR2(n char) |
| java.lang.Number | NUMBER(38) |
| java.math.BigInteger | NUMBER(38) |
| java.math.BigDecimal | NUMBER(38) |
| byte[], java.lang.Byte[], java.sql.Blob | BLOB |
