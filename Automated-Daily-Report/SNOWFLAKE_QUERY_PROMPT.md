# Snowflake Query Prompt for GEP Data Export

## 🎯 Objective
Connect to Snowflake and execute a query to extract GEP (Gusto Embedded Payroll) leads, adds, and company data for reporting and analysis.

---

## 📋 Instructions for AI Assistant

Please help me connect to Snowflake and run the query below to extract GEP data.

### Step 1: Snowflake Connection
Connect to the Gusto Snowflake instance using the following connection parameters:

```
Account: [Your Snowflake Account - e.g., gusto.us-west-2]
Username: [Your Snowflake Username]
Warehouse: [Your Warehouse - e.g., ANALYST_WH or BI_WH]
Database: [Your Database - typically the one containing 'bi' schema]
Role: [Your Role - e.g., ANALYST or appropriate role with access to bi schema]
```

**Authentication Options:**
- SSO (Single Sign-On) - preferred for Gusto employees
- Username/Password
- Key-pair authentication

### Step 2: Execute the Query
Run the SQL query provided in Section 3 below.

### Step 3: Export Results
After the query completes:
1. Export the results to a CSV file named: `gep_data_export_[YYYY-MM-DD].csv`
2. Confirm the row count and date range of the extracted data
3. Provide a summary of the data (e.g., total leads, total adds, date range)

---

## 🗄️ SQL Query

```sql
with dates as ( 
select distinct date_trunc('day', date) as calendar_month, fiscal_year, fiscal_quarter 
from  bi.static_calendar a 
where date between '2021-01-01' and current_date
),
monthly_leads as (
select distinct date_trunc('day', account_created_ts) as action_month
				, date(account_created_ts) as action_date
				, partner_id
				, partner_name
				, company_id
				, company_name
                                , new_to_gusto_payroll
				, 1 as leads
from bi.gep_companies 
	where account_created_ts is not null

--group by 1,2,3,4,5
), 
monthly_adds as (
select distinct date_trunc('day', first_after_enroll_payroll_ts) as action_month
				, date(first_after_enroll_payroll_ts) as action_date
				, partner_id
				, partner_name
				, company_id
				, company_name
                                , new_to_gusto_payroll
				, 1 as adds
                                , datediff('days', account_created_Ts, first_after_enroll_payroll_ts) as days_to_convert
from bi.gep_companies 
 where
  (
      (
        first_after_enroll_payroll_ts is not null 
           and 
        partner_name  in ('Collective','1-800Accountant - Deprecated','Vagaro Embedded Payroll','Freshbooks','Formations','Archy - Deprecated','Heard','Hourly.io','GoCo','Lettuce Financial Labs','HR for Health','Chase')
             and 
        first_after_enroll_payroll_ts < '2025-12-29'
        )
       or 
       (
            first_after_enroll_payroll_ts < coalesce(dissociation_ts,suspension_dt)
             or 
            (first_after_enroll_payroll_ts is not null and coalesce(dissociation_ts,suspension_dt) is null)
       )
    )
), 
monthly_adds_by_created as (
select distinct date_trunc('day', account_created_Ts) as action_month
				, date(first_after_enroll_payroll_ts) as action_date
				, partner_id
				, partner_name
				, company_id
				, company_name
                                , new_to_gusto_payroll
				, 1 as adds
                                , datediff('days', account_created_Ts, first_after_enroll_payroll_ts) as days_to_convert_by_account_created_date
from bi.gep_companies 
	where
        --first_after_enroll_payroll_ts is not null
	--and (dissociation_ts is null or dissociation_ts > first_after_enroll_payroll_ts or suspension_dt > first_after_enroll_payroll_ts)
 (
       (
        first_after_enroll_payroll_ts is not null 
           and 
        partner_name  in ('Collective','1-800Accountant - Deprecated','Vagaro Embedded Payroll','Freshbooks','Formations','Archy - Deprecated','Heard','Hourly.io','GoCo','Lettuce Financial Labs','HR for Health','Chase')
             and 
        first_after_enroll_payroll_ts < '2025-12-29'
        )
       or 
       (
            first_after_enroll_payroll_ts < coalesce(dissociation_ts,suspension_dt)
             or 
            (first_after_enroll_payroll_ts is not null and coalesce(dissociation_ts,suspension_dt) is null)
       )
    )




),base as(

select
      distinct 
       a.fiscal_year
     , a.fiscal_quarter 
     , a.calendar_month
	 , b.action_date
	 , b.partner_id
	 , b.partner_name
	 , b.company_id
	 , b.company_name
         , b.new_to_gusto_payroll
	 , b.leads as leads_flag
	 , 0 as adds_flag
         , 0 as days_to_convert
         , 0 as days_to_convert_by_account_created_date
from dates a 
inner join monthly_leads b
	on a.calendar_month = b.action_month
union
select distinct 
       a.fiscal_year
     , a.fiscal_quarter 
     , a.calendar_month
	 , b.action_date
	 , b.partner_id
	 , b.partner_name
	 , b.company_id
	 , b.company_name
         , b.new_to_gusto_payroll
	 , 0 as leads_flag
	 , b.adds as adds_flag
         , days_to_convert
         , 0 days_to_convert_by_account_created_date
from dates a 
inner join monthly_adds b
	on a.calendar_month = b.action_month

union

select
    a.fiscal_year
     , a.fiscal_quarter 
     , a.calendar_month
     , c.action_date
     , c.partner_id
     , c.partner_name
     , c.company_id
     , c.company_name
     , c.new_to_gusto_payroll
     , 0 as leads_flag
     , 0 as adds_flag
     , 0 days_to_convert
     , days_to_convert_by_account_created_date
from dates a 
inner join monthly_adds_by_created c
	on a.calendar_month = c.action_month
)
select
       b.fiscal_year as "fiscal_year",
       b.fiscal_quarter as "fiscal_quarter",
       b.calendar_month as "calendar_month",
       b.action_date as "action_date",
       b.partner_id as "partner_id",
       b.partner_name as "partner_name",
       b.company_id as "company_id",
       b.company_name as "company_name",
       b.new_to_gusto_payroll as "new_to_gusto_payroll",
       b.leads_flag as "leads_flag",
       b.adds_flag as "adds_flag",
       b.days_to_convert as "days_to_convert",
       b.days_to_convert_by_account_created_date as "days_to_convert_by_account_created_date",
       ly.leads_flag as "leads_flag_ly",
       ly.adds_flag  as "adds_flag_ly",
       c.id as "id",
    c.name as "name",
    c.trade_name as "trade_name",
    c.accounting_firm_id as "accounting_firm_id",
    c.created_at as "created_at",
    c.company_lead_id as "company_lead_id",
    c.initial_company_size as "initial_company_size",
    c.initial_employee_count as "initial_employee_count",
    c.segment_by_initial_size as "segment_by_initial_size",
    c.segment_by_initial_employee_count as "segment_by_initial_employee_count",
    c.initial_contractor_count as "initial_contractor_count",
    c.approval_status as "approval_status",
    c.number_active_employees as "number_active_employees",
    c.number_active_contractors as "number_active_contractors",
    c.segment_by_current_employee_count as "segment_by_current_employee_count",
    c.segment_by_current_size as "segment_by_current_size",
    c.joined_at as "joined_at",
    c.is_active as "is_active",
    c.finished_onboarding_at as "finished_onboarding_at",
    c.originally_finished_onboarding_at as "originally_finished_onboarding_at",
    c.last_finished_onboarding_at as "last_finished_onboarding_at",
    c.suspension_at as "suspension_at",
    c.is_soft_suspended as "is_soft_suspended",
    c.has_suspension_warning as "has_suspension_warning",
    c.suspension_leaving_for as "suspension_leaving_for",
    c.suspension_created_at as "suspension_created_at",
    c.active_wc_policy as "active_wc_policy",
    c.has_zenefits_integration as "has_zenefits_integration",
    c.filing_address_id as "filing_address_id",
    c.filing_state as "filing_state",
    c.filing_city as "filing_city",
    c.filing_zip as "filing_zip",
    c.mailing_address_id as "mailing_address_id",
    c.tax_payer_type as "tax_payer_type",
    c.pass_through as "pass_through",
    c.median_payroll_net_pay as "median_payroll_net_pay",
    c.median_payroll_tax as "median_payroll_tax",
    c.sic_code as "sic_code",
    c.previous_payroll_provider as "previous_payroll_provider",
    c.had_previous_provider as "had_previous_provider",
    c.has_accountant_collaborator as "has_accountant_collaborator",
    c.is_bank_verified as "is_bank_verified",
    c.has_bank_info as "has_bank_info",
    c.from_partner_program as "from_partner_program",
    c.partner_acquisition as "partner_acquisition",
    c.volume_discount_eligible as "volume_discount_eligible",
    c.current_federal_deposit_schedule as "current_federal_deposit_schedule",
    c.is_eftps_enabled as "is_eftps_enabled",
    c.partner_billing as "partner_billing",
    c.bill_to_accountant as "bill_to_accountant",
    c.bill_to_client as "bill_to_client",
    c.bank_account_type as "bank_account_type",
    c.first_approved_at as "first_approved_at",
    c.is_eligible_for_fast_ach as "is_eligible_for_fast_ach",
    c.has_fast_ach as "has_fast_ach",
    c.supports_multiple_pay_schedules as "supports_multiple_pay_schedules",
    c.has_teams as "has_teams",
    c.suggested_referral as "suggested_referral",
    c.suggested_referral_at as "suggested_referral_at",
    c.suggested_referral_by_user as "suggested_referral_by_user",
    c.estimated_company_founded_date as "estimated_company_founded_date",
    c.previous_payroll_provider_type as "previous_payroll_provider_type",
    c.current_flag as "current_flag",
    c.updated_at as "updated_at",
    c.industry_source as "industry_source",
    c.slug as "slug",
    c.previous_payroll_provider_sub_type as "previous_payroll_provider_sub_type",
    c.previous_company_id as "previous_company_id",
    c.is_big_desk as "is_big_desk",
    c.lead_industry_classification as "lead_industry_classification",
    c.is_big_desk_initial as "is_big_desk_initial",
    c.number_active_contractors_current_mtd as "number_active_contractors_current_mtd",
    c.number_active_employees_current_mtd as "number_active_employees_current_mtd",
    c.uuid as "uuid",
    c.has_gws as "has_gws",
    c.is_mrb as "is_mrb",
    c.previous_provider_in as "previous_provider_in",
    c.suspension_id as "suspension_id",
    c.dbt_incremental_ts as "dbt_incremental_ts",
    c.sales_program as "sales_program",
    c.risk_state_description as "risk_state_description",
    c.suspended_reason as "suspended_reason",
    c.naics_code as "naics_code",
    c.user_provided_industry as "user_provided_industry",
    c.user_provided_sub_industry as "user_provided_sub_industry",
    c.industry_classification as "industry_classification",
    c.industry_title as "industry_title",
    c.industry_custom_description as "industry_custom_description",
    c.suggested_referral_channel as "suggested_referral_channel",
    c.bank_name as "bank_name",
    c.snowplow__created_by_user_id as "snowplow__created_by_user_id",
    c.etl_insert_ts as "etl_insert_ts",
    c.etl_update_ts as "etl_update_ts"
from base as b
join bi.companies as c on b.company_id = c.id
left join base as ly
  on ly.partner_id     = b.partner_id
 and ly.company_id     = b.company_id
 and ly.calendar_month = dateadd('year', -1, b.calendar_month)
```

---

## 📊 Query Details

### What This Query Does:
This query extracts comprehensive GEP (Gusto Embedded Payroll) data including:

1. **Leads Data**: Companies that created accounts (from `account_created_ts`)
2. **Adds Data**: Companies that completed their first payroll (from `first_after_enroll_payroll_ts`)
3. **Company Details**: Full company profile information from `bi.companies`
4. **Year-over-Year Comparison**: Previous year metrics for trend analysis

### Key Data Points:
- **Date Range**: 2021-01-01 to current_date
- **Partners Included**: Collective, 1-800Accountant, Vagaro, Freshbooks, Formations, Archy, Heard, Hourly.io, GoCo, Lettuce Financial Labs, HR for Health, Chase
- **Metrics**:
  - `leads_flag`: Indicator for lead creation (1 = lead, 0 = not a lead)
  - `adds_flag`: Indicator for payroll completion (1 = add, 0 = not an add)
  - `days_to_convert`: Days from account creation to first payroll
  - `leads_flag_ly`: Previous year lead indicator
  - `adds_flag_ly`: Previous year add indicator

### Output Columns (106 total):
**Core Metrics:**
- fiscal_year, fiscal_quarter, calendar_month, action_date
- partner_id, partner_name, company_id, company_name
- leads_flag, adds_flag, days_to_convert
- leads_flag_ly, adds_flag_ly (year-over-year comparison)

**Company Attributes:**
- Company identification (id, name, trade_name, uuid)
- Size metrics (initial/current employee count, contractor count)
- Status indicators (is_active, approval_status, suspension info)
- Financial data (median payroll metrics)
- Integration flags (has_zenefits_integration, has_gws)
- Partner relationship (from_partner_program, partner_billing)
- Industry classification (naics_code, industry_classification)
- And 80+ additional company attributes...

---

## ✅ Expected Output

After running the query, you should receive:

1. **Row Count**: Approximately 50,000 - 500,000 rows (depending on data volume)
2. **Date Range**: Data from 2021-01-01 to today
3. **Column Count**: 106 columns

### Sample Summary to Provide:
```
Query Execution Summary:
- Total Rows: [X]
- Date Range: 2021-01-01 to [today's date]
- Total Leads: [sum of leads_flag]
- Total Adds: [sum of adds_flag]
- Unique Partners: [count distinct partner_name]
- Unique Companies: [count distinct company_id]
- Execution Time: [X] seconds
```

---

## 🔧 Troubleshooting

**If you encounter connection issues:**
1. Verify you have access to the `bi` schema
2. Confirm your warehouse is running
3. Check that your role has SELECT permissions on `bi.gep_companies` and `bi.companies`

**If the query times out:**
1. Increase warehouse size temporarily (e.g., from XS to M)
2. Consider adding a date filter to the final query to limit results
3. Run query during off-peak hours

**If you see permission errors:**
1. Request access to the BI schema from your data team
2. Ensure your role includes ANALYST or similar permissions

---

## 📁 File Naming Convention

Save the export as:
```
gep_data_export_[YYYY-MM-DD].csv
```

Example: `gep_data_export_2026-01-07.csv`

---

## 🚀 Quick Start Command

If using Snowflake CLI (SnowSQL):

```bash
snowsql -a [account] -u [username] -d [database] -w [warehouse] -f snowflake_gep_query.sql -o output_file=gep_data_export_$(date +%Y-%m-%d).csv -o header=true -o output_format=csv
```

---

## 📞 Support

For questions about this query or data access:
- **Data Team**: [Your data team contact/channel]
- **Snowflake Access**: Submit request via [your internal process]
- **Query Author**: Victor Sanabia (victor.sanabia@gusto.com)

---

## 📝 Notes

- This query joins the base CTE with the full `bi.companies` table, so it may take 1-3 minutes to execute
- The query includes both current year and last year (ly) metrics for YoY analysis
- Date filtering uses `current_date`, so it automatically updates each day
- The `first_after_enroll_payroll_ts < '2025-12-29'` filter is a specific business rule for certain partners

---

**Version:** 1.0  
**Last Updated:** January 7, 2026  
**Created by:** Victor Sanabia


