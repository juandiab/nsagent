<template>
  <section id="solutions" class="landing-section-tight">
    <div class="landing-container landing-solutions">
      <div class="landing-solution-block">
        <div class="landing-solution-copy landing-solution-copy-light">
          <span class="landing-badge">Operations</span>
          <h2 class="landing-solution-title">From design to execution</h2>
          <p class="landing-solution-lead">
            Start in Architect for structured discovery and formal design documents, then hand off to Operator
            for implementation — without leaving the conversation.
          </p>
          <ul class="landing-check-list landing-check-list-light">
            <li><i class="pi pi-check-circle" /><span>Guided `jpilot-form` blocks for load balancers and policies</span></li>
            <li><i class="pi pi-check-circle" /><span>Send to Operator from design deliverables in one click</span></li>
            <li><i class="pi pi-check-circle" /><span>Memory-guided RAG gates API and CLI usage before execution</span></li>
          </ul>
        </div>
        <div class="landing-solution-visual" aria-hidden="true">
          <img
            :src="startupFeatureImg1"
            alt=""
            class="landing-solution-visual-image"
          />
        </div>
      </div>

      <div class="landing-solution-block landing-solution-block-reverse">
        <div class="landing-solution-copy landing-solution-copy-light">
          <span class="landing-badge">Reliability</span>
          <h2 class="landing-solution-title">Troubleshoot with context</h2>
          <p class="landing-solution-lead">
            Analyst mode stays read-first while diagnostics, official documentation search, and appliance telemetry
            keep investigations grounded in your environment.
          </p>
          <ul class="landing-check-list landing-check-list-light">
            <li><i class="pi pi-check-circle" /><span>NetScaler ping, traceroute, port checks, and `nsconmsg` collection</span></li>
            <li><i class="pi pi-check-circle" /><span>Brave Search limited to vendor official domains per platform</span></li>
            <li><i class="pi pi-check-circle" /><span>Dual-pane chat with model-aware context usage rings</span></li>
          </ul>
        </div>
        <div class="landing-solution-visual" aria-hidden="true">
          <img
            :src="startupFeatureImg2"
            alt=""
            class="landing-solution-visual-image"
          />
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import startupFeatureImg1 from '../../assets/landing/startup-feature-img-1.png'
import startupFeatureImg2 from '../../assets/landing/startup-feature-img-2.png'
</script>

<style scoped>
.landing-solutions {
  display: flex;
  flex-direction: column;
  gap: 5rem;
}

.landing-solution-block {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2.5rem;
  align-items: center;
}

.landing-solution-copy {
  max-width: 34rem;
}

.landing-solution-copy-light .landing-check-list-light li {
  color: var(--landing-text-muted);
}

.landing-solution-copy-light .landing-check-list-light .pi {
  color: var(--p-primary-color);
}

.landing-solution-title {
  margin: 1rem 0 0;
  font-size: clamp(1.75rem, 3vw, 2.5rem);
  font-weight: 700;
  line-height: 1.12;
  color: var(--landing-text);
}

.landing-solution-lead {
  margin: 1rem 0 0;
  line-height: 1.65;
  color: var(--landing-text-muted);
}

.landing-check-list-light {
  list-style: none;
  margin: 2rem 0 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.landing-check-list-light li {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  font-size: 1rem;
  line-height: 1.5;
}

.landing-check-list-light .pi {
  margin-top: 0.2rem;
}

.landing-solution-visual {
  position: relative;
  width: min(100%, 35rem);
  height: 23rem;
  margin-inline: auto;
  border-radius: var(--landing-radius-xl);
  background: linear-gradient(180deg, var(--landing-hero-from) 0%, var(--landing-hero-to) 100%);
  box-shadow: var(--landing-card-shadow);
  overflow: hidden;
}

.landing-solution-visual-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: auto;
  max-width: none;
}

@media (min-width: 960px) {
  .landing-solutions {
    gap: 8rem;
  }

  .landing-solution-block {
    grid-template-columns: 1fr 1fr;
    gap: 3rem;
  }

  .landing-solution-block-reverse .landing-solution-copy {
    order: 2;
  }

  .landing-solution-block-reverse .landing-solution-visual {
    order: 1;
  }

  .landing-solution-visual {
    height: 31rem;
    margin-inline: 0;
  }
}
</style>
