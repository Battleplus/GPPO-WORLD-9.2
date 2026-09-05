from copy import deepcopy
import torch
from gppo_world.jepa_two_stage import NodeEncoder,ActionDynamics,MaskedPretrainer,masked_graph
from gppo_world.jepa import batch_graphs
from test_contracts import make_graph


def test_mask_clears_duplicate_relations_and_preserves_source():
    g=batch_graphs([make_graph(),make_graph()]);old=deepcopy(g)
    for x in g['edge_attr'].values():x.fill_(1)
    masked,mask=masked_graph(g,torch.Generator().manual_seed(12))
    assert mask.sum(1).min()>=3
    assert all(torch.count_nonzero(x)==0 for x in masked['edge_attr'].values())
    assert all(torch.all(x==1) for x in g['edge_attr'].values())
    assert all(torch.equal(g['nodes'][k],v) for k,v in old['nodes'].items())


def arguments():
    torch.manual_seed(8)
    return dict(tokens=torch.randn(2,4,11,64),valid=torch.ones(2,4,dtype=torch.bool),
        past_actions=torch.tensor([[1,2,3,-1],[2,1,0,-1]]),past_gaps=torch.zeros(2,4),
        candidate_edges=torch.tensor([[(u,r) for u in range(4) for r in range(4)]]*2),
        edge_attributes=torch.randn(2,16,5),action=torch.tensor([1,2]),evidence=torch.zeros(2,14))


def test_no_action_ablation_does_not_read_any_candidate_information():
    model=ActionDynamics(with_action=False);a=arguments();b=deepcopy(a)
    b['action']=torch.tensor([16,8]);b['candidate_edges'].fill_(999);b['edge_attributes'].normal_()
    assert torch.equal(model(**a),model(**b))


def test_endpoint_mapping_noop_and_padding():
    model=ActionDynamics();a=arguments();a['valid'][:,:2]=False
    b=deepcopy(a);b['tokens'][:,:2].normal_(100,10);b['past_actions'][:,:2]=7;b['past_gaps'][:,:2]=999
    assert torch.equal(model(**a),model(**b))
    b=deepcopy(a);b['action']=torch.tensor([16,16]);c=deepcopy(b);c['edge_attributes'].fill_(999)
    assert torch.equal(model(**b),model(**c))
    b=deepcopy(a);b['action']=torch.tensor([8,15]);assert not torch.equal(model(**a),model(**b))


def test_pretraining_target_no_grad_and_graph_shapes():
    model=MaskedPretrainer();g=batch_graphs([make_graph(),make_graph()])
    loss=model.loss(g,torch.Generator().manual_seed(7));loss.backward()
    assert torch.isfinite(loss)
    assert model.encoder(g).shape==(2,11,64)
    assert all(p.grad is None for p in model.target.parameters())
