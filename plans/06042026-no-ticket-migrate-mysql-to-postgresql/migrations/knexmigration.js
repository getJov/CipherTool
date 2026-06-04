// CipherTool Knex equivalent migration.
// Runtime target remains Flask + Supabase PostgreSQL; this is maintained for
// plan parity only.

exports.up = async function up(knex) {
  const exists = await knex.schema.hasTable('users');

  if (!exists) {
    await knex.schema.createTable('users', (table) => {
      table.increments('id').primary();
      table.string('username', 255).notNullable();
      table.string('password', 255).notNullable();
      table.integer('login_attempts').notNullable().defaultTo(0);
      table.boolean('blocked').notNullable().defaultTo(false);
      table.string('totp_secret', 64).nullable();
    });
  } else {
    const hasTotpSecret = await knex.schema.hasColumn('users', 'totp_secret');

    if (!hasTotpSecret) {
      await knex.schema.alterTable('users', (table) => {
        table.string('totp_secret', 64).nullable();
      });
    }
  }
};

exports.down = async function down(knex) {
  const exists = await knex.schema.hasTable('users');

  if (exists) {
    const hasTotpSecret = await knex.schema.hasColumn('users', 'totp_secret');

    if (hasTotpSecret) {
      await knex.schema.alterTable('users', (table) => {
        table.dropColumn('totp_secret');
      });
    }
  }
};
