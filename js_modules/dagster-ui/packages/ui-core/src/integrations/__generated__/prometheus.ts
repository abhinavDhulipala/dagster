/**
 * THIS FILE IS GENERATED BY `yarn generate-integration-docs`.
 *
 * DO NOT EDIT MANUALLY.
 */

import {IntegrationFrontmatter} from '../types';
import prometheusLogo from './logos/prometheus.svg';

export const logo = prometheusLogo;

export const frontmatter: IntegrationFrontmatter = {
  id: 'prometheus',
  status: 'published',
  name: 'Prometheus',
  title: 'Dagster & Prometheus',
  excerpt: 'Integrate with Prometheus via the prometheus_client library.',
  partnerlink: '',
  categories: ['Monitoring'],
  enabledBy: [],
  enables: [],
  tags: ['dagster-supported', 'monitoring'],
};

export const content =
  'import Beta from \'@site/docs/partials/\\_Beta.md\';\n\n<Beta />\n\nThis integration allows you to push metrics to the Prometheus gateway from within a Dagster pipeline.\n\n### Installation\n\n```bash\npip install dagster-prometheus\n```\n\n### Example\n\n\n```python\nfrom dagster_prometheus import PrometheusResource\n\nimport dagster as dg\n\n\n@dg.asset\ndef prometheus_metric(prometheus: PrometheusResource):\n    prometheus.push_to_gateway(job="my_job_label")\n\n\ndefs = dg.Definitions(\n    assets=[prometheus_metric],\n    resources={\n        "prometheus": PrometheusResource(gateway="http://pushgateway.example.org:9091")\n    },\n)\n```\n        \n\n### About Prometheus\n\n**Prometheus** is an open source systems monitoring and alerting toolkit. Originally built at SoundCloud, Prometheus joined the Cloud Native Computing Foundation in 2016 as the second hosted project, after Kubernetes.\n\nPrometheus collects and stores metrics as time series data along with the timestamp at which it was recorded, alongside optional key-value pairs called labels.';
