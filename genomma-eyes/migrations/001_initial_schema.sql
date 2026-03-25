-- Genomma Eyes - Schema inicial
-- Ejecutar en Supabase SQL Editor

-- ============================================================
-- TABLA: employees
-- ============================================================
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    area TEXT,
    country TEXT NOT NULL,
    whatsapp TEXT UNIQUE NOT NULL,
    total_points INTEGER DEFAULT 0,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_employees_whatsapp ON employees(whatsapp);
CREATE INDEX idx_employees_country ON employees(country);

-- ============================================================
-- TABLA: quests (misiones especiales)
-- ============================================================
CREATE TABLE IF NOT EXISTS quests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    prize_amount NUMERIC(10, 2),
    countries TEXT[] DEFAULT '{}',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    target_brand TEXT,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_quests_active ON quests(active, start_date, end_date);

-- ============================================================
-- TABLA: visits (cada foto enviada)
-- ============================================================
CREATE TABLE IF NOT EXISTS visits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    photo_url TEXT,
    lat DOUBLE PRECISION,
    lng DOUBLE PRECISION,
    country TEXT,
    store_type TEXT CHECK (store_type IN ('super', 'farmacia', 'conveniencia', 'tradicional', 'otro')),
    store_name TEXT,
    ai_analysis JSONB,
    points_earned INTEGER DEFAULT 0,
    quest_id UUID REFERENCES quests(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_visits_employee ON visits(employee_id, created_at DESC);
CREATE INDEX idx_visits_country ON visits(country, created_at DESC);
CREATE INDEX idx_visits_store_type ON visits(store_type);

-- ============================================================
-- TABLA: monthly_checklist
-- ============================================================
CREATE TABLE IF NOT EXISTS monthly_checklist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    month TEXT NOT NULL, -- formato: '2026-03'
    has_super BOOLEAN DEFAULT false,
    has_farmacia BOOLEAN DEFAULT false,
    has_tradicional BOOLEAN DEFAULT false,
    has_conveniencia BOOLEAN DEFAULT false,
    eligible_for_prize BOOLEAN DEFAULT false,
    UNIQUE(employee_id, month)
);

CREATE INDEX idx_checklist_month ON monthly_checklist(month, eligible_for_prize);

-- ============================================================
-- TABLA: alerts (alertas críticas detectadas)
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    visit_id UUID NOT NULL REFERENCES visits(id),
    employee_id UUID NOT NULL REFERENCES employees(id),
    alert_type TEXT NOT NULL,
    description TEXT,
    country TEXT,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_alerts_unresolved ON alerts(resolved, created_at DESC);

-- ============================================================
-- FUNCIÓN: actualizar updated_at automáticamente
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- RLS (Row Level Security) básico
-- ============================================================
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE visits ENABLE ROW LEVEL SECURITY;
ALTER TABLE quests ENABLE ROW LEVEL SECURITY;
ALTER TABLE monthly_checklist ENABLE ROW LEVEL SECURITY;
ALTER TABLE alerts ENABLE ROW LEVEL SECURITY;

-- Política: service_role puede todo (el backend usa service key)
CREATE POLICY "Service role full access" ON employees FOR ALL USING (true);
CREATE POLICY "Service role full access" ON visits FOR ALL USING (true);
CREATE POLICY "Service role full access" ON quests FOR ALL USING (true);
CREATE POLICY "Service role full access" ON monthly_checklist FOR ALL USING (true);
CREATE POLICY "Service role full access" ON alerts FOR ALL USING (true);

-- ============================================================
-- STORAGE: bucket para fotos de visitas
-- ============================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('visit-photos', 'visit-photos', true)
ON CONFLICT (id) DO NOTHING;
