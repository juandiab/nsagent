<template>
  <section id="features" class="landing-section">
    <div class="landing-container landing-features">
      <div class="landing-features-head">
        <span class="landing-eyebrow">Platform capabilities</span>
        <h2 class="landing-title">Built for infrastructure teams</h2>
        <p class="landing-lead">
          Inventory appliances, connect local or enterprise LLMs, and run vendor-aware automation from a single
          control plane — with skills shaped by infrastructure SME engineers, not generic chatbots.
        </p>
      </div>

      <div class="landing-features-showcase">
        <div class="landing-features-showcase-media">
          <img
            :src="saasFeatureImg2"
            alt="JPilot platform dashboard preview"
            class="landing-features-showcase-image"
          />
        </div>
        <div class="landing-features-showcase-copy">
          <h3>Enterprise isolation</h3>
          <p>
            Point JPilot at a local model (LM Studio) or your enterprise LLM (Azure OpenAI, AWS Bedrock, private
            endpoints). Traffic and appliance context stay inside your infrastructure — not a shared SaaS pool.
          </p>
        </div>
      </div>

      <div class="landing-features-grid">
        <article v-for="feature in features" :key="feature.title" class="landing-card landing-feature-card">
          <div class="landing-feature-icon">
            <i :class="feature.icon" />
          </div>
          <h3>{{ feature.title }}</h3>
          <p>{{ feature.description }}</p>
        </article>
      </div>
    </div>
  </section>
</template>

<script setup>
import saasFeatureImg2 from '../../assets/landing/saas-feature-img-2.png'

const features = [
  {
    icon: 'pi pi-server',
    title: 'Multi-vendor inventory',
    description: 'Register NetScaler ADC, SDX, Cisco IOS/XE, and F5 BIG-IP with encrypted credentials and tags for filtering.'
  },
  {
    icon: 'pi pi-sparkles',
    title: 'JPilot chat roles',
    description: 'Architect, Operator, and Analyst personas with tool-calling bound to the selected appliance — credentials never sent to the LLM.'
  },
  {
    icon: 'pi pi-key',
    title: 'Bring your own keys',
    description: 'Connect OpenAI, Anthropic, Gemini, Azure OpenAI, AWS Bedrock, OpenRouter, or a local endpoint. You choose the provider and pay for inference.'
  },
  {
    icon: 'pi pi-book',
    title: 'SME engineer skills',
    description: 'Architect, Operator, and Analyst workflows, prompts, and memory files are built from NetScaler, Cisco, and F5 SME practice — plus ~200 recommended actions in the command menu.'
  },
  {
    icon: 'pi pi-wrench',
    title: 'MCP tool server',
    description: 'Next-Gen API, classic CLI over SSH, NITRO helpers, diagnostics, and SSL CSR generation exposed to the agent.'
  },
  {
    icon: 'pi pi-shield',
    title: 'Enterprise-ready auth',
    description: 'Password login, optional passkeys, account recovery, and admin user management with role-based access.'
  },
  {
    icon: 'pi pi-chart-line',
    title: 'Usage visibility',
    description: 'Track monthly LLM token usage and Brave Search queries locally so teams can monitor adoption and cost drivers.'
  }
]
</script>

<style scoped>
.landing-features-head {
  max-width: 40rem;
  margin-inline: auto;
  text-align: center;
}

.landing-features-head .landing-title {
  margin-top: 0.75rem;
}

.landing-features-head .landing-lead {
  margin-top: 1rem;
}

.landing-features {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.landing-features-showcase {
  display: flex;
  flex-direction: column;
  width: min(100%, 30rem);
  min-height: 29rem;
  margin-top: 3rem;
  border-radius: var(--landing-radius-xl);
  background: linear-gradient(180deg, var(--landing-hero-from) 0%, var(--landing-hero-to) 100%);
  box-shadow: var(--landing-card-shadow);
  overflow: hidden;
}

.landing-features-showcase-media {
  display: flex;
  flex: 1 1 auto;
  justify-content: center;
  align-items: center;
  width: 100%;
  padding: 2rem 1.5rem 0;
}

.landing-features-showcase-image {
  display: block;
  width: 100%;
  max-width: 29.125rem;
  height: auto;
  margin-inline: auto;
}

.landing-features-showcase-copy {
  margin-top: auto;
  padding: 1.25rem 1.5rem 1.75rem;
  text-align: center;
  color: var(--landing-text-on-hero);
}

.landing-features-showcase-copy h3 {
  margin: 0;
  font-size: 1.375rem;
  font-weight: 700;
  line-height: 1.25;
}

.landing-features-showcase-copy p {
  margin: 0.75rem 0 0;
  font-size: 0.9375rem;
  line-height: 1.6;
  color: var(--landing-text-muted-on-hero);
}

.landing-features-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1.25rem;
  margin-top: 3rem;
  width: 100%;
}

.landing-feature-card {
  box-sizing: border-box;
  flex: 0 1 100%;
  padding: 1.75rem;
}

.landing-feature-card h3 {
  margin: 1.25rem 0 0;
  font-size: 1.25rem;
  font-weight: 700;
}

.landing-feature-card p {
  margin: 0.875rem 0 0;
  color: var(--landing-text-muted);
  line-height: 1.6;
}

.landing-feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 3.25rem;
  height: 3.25rem;
  border-radius: 1rem;
  background: linear-gradient(180deg, var(--landing-hero-from), var(--landing-hero-to));
  color: var(--landing-primary);
  box-shadow: inset 0 2px 3px rgba(255, 255, 255, 0.18);
}

.landing-feature-icon .pi {
  font-size: 1.25rem;
}

@media (min-width: 640px) {
  .landing-feature-card {
    flex-basis: calc((100% - 1.25rem) / 2);
  }
}

@media (min-width: 1024px) {
  .landing-feature-card {
    flex-basis: calc((100% - 2 * 1.25rem) / 3);
  }

  .landing-features-showcase {
    width: min(100%, 42rem);
    min-height: 37rem;
    margin-top: 3.5rem;
  }

  .landing-features-showcase-media {
    padding: 3rem 2rem 0;
  }

  .landing-features-showcase-image {
    max-width: 29.125rem;
  }

  .landing-features-showcase-copy h3 {
    font-size: 1.5rem;
  }

  .landing-features-showcase-copy p {
    font-size: 1.0625rem;
  }
}
</style>
